package com.example.stage.Model;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Document(collection = "pointage")
public class Pointage {

    @Id
    private String id;

    private String user_id;
    private String username;

    private LocalDate date_pointage;
    private LocalDateTime heure_pointage;

    private String statut;

    private Localisation localisation;

    private String adresse;

    public String getUser_id() {
        return user_id;
    }

    public void setUser_id(String user_id) {
        this.user_id = user_id;
    }

    public LocalDate getDate_pointage() {
        return date_pointage;
    }

    public void setDate_pointage(LocalDate date_pointage) {
        this.date_pointage = date_pointage;
    }

    public LocalDateTime getHeure_pointage() {
        return heure_pointage;
    }

    public void setHeure_pointage(LocalDateTime heure_pointage) {
        this.heure_pointage = heure_pointage;
    }

    public static class Localisation {
        private double lat;
        private double lon;

        public double getLat() { return lat; }
        public void setLat(double lat) { this.lat = lat; }

        public double getLon() { return lon; }
        public void setLon(double lon) { this.lon = lon; }
    }

    // Getters and Setters pour Pointage
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }


    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }


    public String getStatut() { return statut; }
    public void setStatut(String statut) { this.statut = statut; }

    public Localisation getLocalisation() { return localisation; }
    public void setLocalisation(Localisation localisation) { this.localisation = localisation; }

    public String getAdresse() { return adresse; }
    public void setAdresse(String adresse) { this.adresse = adresse; }
}
