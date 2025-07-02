package com.example.stage.Controller;

import com.example.stage.Model.User;
import com.example.stage.service.UserService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;

@RestController
@CrossOrigin(origins = "*")
@RequestMapping("/users")
public class UserController {

    private final UserService userService;
    private final ObjectMapper objectMapper = new ObjectMapper();
    private static final String UPLOAD_DIR = "uploads/";

    public UserController(UserService userService) {
        this.userService = userService;
    }

    // Create user with photo (multipart/form-data)
    @PostMapping(consumes = {"multipart/form-data"})
    public ResponseEntity<?> createUserWithPhoto(
            @RequestParam("file") MultipartFile file,
            @RequestParam("user") String userJson) {
        try {
            if (file == null || file.isEmpty()) {
                return ResponseEntity.badRequest().body("Photo requise");
            }
            // Create upload directory if not exists
            Files.createDirectories(Paths.get(UPLOAD_DIR));

            String originalFilename = file.getOriginalFilename();
            String filename = System.currentTimeMillis() + "_" + originalFilename;
            Path filePath = Paths.get(UPLOAD_DIR + filename);
            Files.write(filePath, file.getBytes());

            User user = objectMapper.readValue(userJson, User.class);
            if (user == null) {
                return ResponseEntity.badRequest().body("Données utilisateur invalides");
            }

            user.setPhoto(filename);

            User createdUser = userService.createUser(user);

            return ResponseEntity.status(HttpStatus.CREATED).body(createdUser);

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Erreur lors de la création de l'utilisateur");
        }
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
