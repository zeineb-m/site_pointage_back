package com.example.stage.service;

import com.example.stage.Model.Notification;
import com.example.stage.Repository.NotificationRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class NotificationService {

    private final NotificationRepository repository;


    public NotificationService(NotificationRepository repository) {
        this.repository = repository;

    }

    public List<Notification> getAll() {
        return repository.findAll();
    }
    public Notification getById(String id) {
        return repository.findById(id).orElse(null);
    }
    public Notification updateNotification(String id, Notification updatedNotif) {
        Notification notif = repository.findById(id).orElseThrow();
        notif.setStatut(updatedNotif.getStatut());
        notif.setIsRead(updatedNotif.isRead());

        return repository.save(notif);
    }

    public List<Notification> getUnreadByRole(String role) {
        if ("HR".equalsIgnoreCase(role)) {
            // HR voit toutes les notifications non lues
            return repository.findByIsReadFalse();
        }
        // sinon, on filtre par rôle exact
        return repository.findByRoleAndIsReadFalse(role);
    }


    public Notification save(Notification notification) {
        return repository.save(notification);
    }

}
