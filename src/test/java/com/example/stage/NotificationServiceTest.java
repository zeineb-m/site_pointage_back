package com.example.stage;


import com.example.stage.Model.Notification;
import com.example.stage.Repository.NotificationRepository;
import com.example.stage.service.NotificationService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import java.util.Arrays;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class NotificationServiceTest {

    private NotificationRepository repository;
    private NotificationService service;

    @BeforeEach
    void setUp() {
        repository = mock(NotificationRepository.class);
        service = new NotificationService(repository);
    }

    @Test
    void testGetAll() {
        List<Notification> mockList = Arrays.asList(new Notification(), new Notification());
        when(repository.findAll()).thenReturn(mockList);

        List<Notification> result = service.getAll();

        assertEquals(2, result.size());
        verify(repository, times(1)).findAll();
    }

    @Test
    void testGetById_Found() {
        Notification notif = new Notification();
        notif.setId("123");
        when(repository.findById("123")).thenReturn(Optional.of(notif));

        Notification result = service.getById("123");

        assertNotNull(result);
        assertEquals("123", result.getId());
        verify(repository).findById("123");
    }

    @Test
    void testGetById_NotFound() {
        when(repository.findById("456")).thenReturn(Optional.empty());

        Notification result = service.getById("456");

        assertNull(result);
    }

    @Test
    void testSave() {
        Notification notif = new Notification();
        notif.setStatut("test");
        when(repository.save(notif)).thenReturn(notif);

        Notification result = service.save(notif);

        assertEquals("test", result.getStatut());
        verify(repository).save(notif);
    }

    @Test
    void testUpdateNotification() {
        Notification existing = new Notification();
        existing.setId("123");
        existing.setStatut("old");
        existing.setIsRead(false);

        Notification updated = new Notification();
        updated.setStatut("new");
        updated.setIsRead(true);

        when(repository.findById("123")).thenReturn(Optional.of(existing));
        when(repository.save(any(Notification.class))).thenAnswer(i -> i.getArguments()[0]);

        Notification result = service.updateNotification("123", updated);

        assertEquals("new", result.getStatut());
        assertTrue(result.isRead());
        verify(repository).save(existing);
    }

    @Test
    void testGetUnreadByRole_HR() {
        List<Notification> unreadList = Arrays.asList(new Notification(), new Notification());
        when(repository.findByIsReadFalse()).thenReturn(unreadList);

        List<Notification> result = service.getUnreadByRole("HR");

        assertEquals(2, result.size());
        verify(repository).findByIsReadFalse();
    }

    @Test
    void testGetUnreadByRole_Other() {
        List<Notification> roleFiltered = List.of(new Notification());
        when(repository.findByRoleAndIsReadFalse("site_supervisor")).thenReturn(roleFiltered);

        List<Notification> result = service.getUnreadByRole("site_supervisor");

        assertEquals(1, result.size());
        verify(repository).findByRoleAndIsReadFalse("site_supervisor");
    }
}
