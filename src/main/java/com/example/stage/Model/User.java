package com.example.stage.Model;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

@Document(collection = "user")
public class User {

    @Id
    private String id;
    private String username;
    private String email;
    private String password;
    private Role role;
    private String photo;
    private String supervisorId;
    private String photoHash;
    public User() {}

    public User(String id, String username, String email, String password, Role role, String photo, String supervisorId, String photoHash) {
        this.id = id;
        this.username = username;
        this.email = email;
        this.password = password;
        this.role = role;
        this.photo = photo;
        this.supervisorId = supervisorId;
        this.photoHash = photoHash;
    }

    // Getters et Setters

    public String getId() {
        return id;
    }
    public void setId(String id) {
        this.id = id;
    }
    public String getUsername() {
        return username;
    }
    public void setUsername(String username) {
        this.username = username;
    }
    public String getEmail() {
        return email;
    }
    public void setEmail(String email) {
        this.email = email;
    }
    public String getPassword() {
        return password;
    }
    public void setPassword(String password) {
        this.password = password;
    }
    public Role getRole() {
        return role;
    }
    public void setRole(Role role) {
        this.role = role;
    }
    public String getPhoto() {
        return photo;
    }
    public void setPhoto(String photo) {
        this.photo = photo;
    }

    public String getSupervisorId() {
        return supervisorId;
    }

    public void setSupervisorId(String supervisorId) {
        this.supervisorId = supervisorId;
    }
    public String getPhotoHash() {
        return photoHash;
    }
    public void setPhotoHash(String photoHash) {
        this.photoHash = photoHash;
    }
}
