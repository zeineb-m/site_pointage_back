package com.example.stage.Controller;

import com.example.stage.Model.Role;
import com.example.stage.Model.User;
import com.example.stage.service.UserService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.*;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;


import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

@RestController
@CrossOrigin(origins = "*")
@RequestMapping("/users")
public class UserController {

    private final UserService userService;
    private final ObjectMapper objectMapper = new ObjectMapper();
    private static final String UPLOAD_DIR = "uploads/";
    @Autowired
    private RestTemplate restTemplate;
    public UserController(UserService userService) {
        this.userService = userService;
    }

    // Create user
    @PostMapping(consumes = {"multipart/form-data"})
    public ResponseEntity<?> createUserWithPhoto(
            @RequestParam("file") MultipartFile file,
            @RequestParam("user") String userJson,
            @RequestParam("creatorId") String creatorId) {

        try {
            if (file.isEmpty()) {
                return ResponseEntity.badRequest()
                        .body(Collections.singletonMap("messages", Arrays.asList("Photo requise")));
            }

            byte[] fileBytes = file.getBytes();
            String photoHash = md5Hash(fileBytes);

            Files.createDirectories(Paths.get(UPLOAD_DIR));
            String originalFilename = file.getOriginalFilename();
            String filename = System.currentTimeMillis() + "_" + originalFilename;
            Path filePath = Paths.get(UPLOAD_DIR + filename);
            Files.write(filePath, fileBytes);

            User user = objectMapper.readValue(userJson, User.class);
            if (user == null) {
                return ResponseEntity.badRequest()
                        .body(Collections.singletonMap("messages", Arrays.asList("Données utilisateur invalides")));
            }

            if (user.getRole() == Role.EMPLOYEE) {
                user.setSupervisorId(creatorId);
            }
            user.setPhoto(filename);
            user.setPhotoHash(photoHash);  // <-- stocker hash


            LinkedMultiValueMap<String, Object> map = new LinkedMultiValueMap<>();
            map.add("user", userJson);

            ByteArrayResource fileAsResource = new ByteArrayResource(fileBytes) {
                @Override
                public String getFilename() {
                    return originalFilename;
                }
            };
            map.add("file", fileAsResource);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);

            HttpEntity<LinkedMultiValueMap<String, Object>> requestEntity = new HttpEntity<>(map, headers);

            String flaskUrl = "http://localhost:5001/validate-user";
            RestTemplate restTemplate = new RestTemplate();
            ResponseEntity<Map> flaskResponse = restTemplate.postForEntity(flaskUrl, requestEntity, Map.class);

            if (!flaskResponse.getStatusCode().is2xxSuccessful()) {
                return ResponseEntity.badRequest().body(flaskResponse.getBody());
            }

            User createdUser = userService.createUser(user);
            return ResponseEntity.status(HttpStatus.CREATED).body(createdUser);

        } catch (HttpClientErrorException e) {
            String responseBody = e.getResponseBodyAsString();
            ObjectMapper mapper = new ObjectMapper();
            Map<String, Object> errorResponse;
            try {
                errorResponse = mapper.readValue(responseBody, Map.class);
            } catch (Exception ex) {
                errorResponse = Collections.singletonMap("messages", Arrays.asList("Erreur validation IA inconnue."));
            }
            return ResponseEntity.badRequest().body(errorResponse);

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Collections.singletonMap("messages", Arrays.asList("plusieurs champs sont manquants ou invalides.")));
        }
    }
    private String md5Hash(byte[] data) throws NoSuchAlgorithmException {
        MessageDigest md = MessageDigest.getInstance("MD5");
        byte[] digest = md.digest(data);
        StringBuilder sb = new StringBuilder();
        for (byte b : digest) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }

    // Get photo by filename
    @GetMapping("/photo/{filename:.+}")
    public ResponseEntity<Resource> getPhoto(@PathVariable String filename) {
        try {
            Path filePath = Paths.get(UPLOAD_DIR).resolve(filename).normalize();
            Resource resource = new UrlResource(filePath.toUri());
            if (resource.exists()) {
                return ResponseEntity.ok()
                        .contentType(MediaType.IMAGE_JPEG)
                        .body(resource);
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (IOException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    // Get all users
    @GetMapping
    public ResponseEntity<List<User>> getAll() {
        List<User> users = userService.getAllUsers();
        return ResponseEntity.ok(users);
    }

    // Get user by id
    @GetMapping("/{id}")
    public ResponseEntity<?> getById(@PathVariable String id) {
        User user = userService.getUserById(id);
        if (user == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(user);
    }

    // Delete user by id
    @DeleteMapping("/{id}")
    public ResponseEntity<?> delete(@PathVariable String id) {
        try {
            userService.deleteUser(id);
            return ResponseEntity.noContent().build();
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Erreur lors de la suppression");
        }
    }

    // Update user with optional photo update
    @PutMapping(value = "/{id}", consumes = {"multipart/form-data"})
    public ResponseEntity<?> updateUserWithPhoto(
            @PathVariable String id,
            @RequestParam(value = "file", required = false) MultipartFile file,
            @RequestParam("user") String userJson) {
        try {
            User existingUser = userService.getUserById(id);
            if (existingUser == null) {
                return ResponseEntity.notFound().build();
            }

            User userUpdates = objectMapper.readValue(userJson, User.class);

            if (file != null && !file.isEmpty()) {
                Files.createDirectories(Paths.get(UPLOAD_DIR));
                String originalFilename = file.getOriginalFilename();
                String filename = System.currentTimeMillis() + "_" + originalFilename;
                Path filePath = Paths.get(UPLOAD_DIR + filename);
                Files.write(filePath, file.getBytes());
                userUpdates.setPhoto(filename);
            } else {
                userUpdates.setPhoto(existingUser.getPhoto());
            }

            userUpdates.setId(id);
            User updatedUser = userService.updateUser(userUpdates);
            return ResponseEntity.ok(updatedUser);

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Erreur lors de la mise à jour");
        }
    }

    // Sign in endpoint
    @PostMapping("/signin")
    public ResponseEntity<?> signIn(@RequestBody Map<String, String> credentials) {
        String email = credentials.get("email");
        String password = credentials.get("password");

        User user = userService.authenticate(email, password);
        if (user != null) {
            return ResponseEntity.ok(user);
        } else {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("Email ou mot de passe incorrect");
        }
    }
}
