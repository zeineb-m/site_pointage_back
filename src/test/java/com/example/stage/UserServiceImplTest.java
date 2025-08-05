package com.example.stage;


import com.example.stage.Model.Role;
import com.example.stage.Model.User;
import com.example.stage.Repository.UserRepository;

import com.example.stage.service.UserServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;

import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserServiceImplTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserServiceImpl userService;

    private User user1;
    private User user2;

    @BeforeEach
    void setUp() {
        user1 = new User();
        user1.setId("1");
        user1.setUsername("Alice");
        user1.setEmail("alice@example.com");
        user1.setRole(Role.EMPLOYEE);

        user2 = new User();
        user2.setId("2");
        user2.setUsername("Bob");
        user2.setEmail("bob@example.com");
        user2.setRole(Role.SITE_SUPERVISOR);
    }

    @Test
    void testGetAllUsers() {
        when(userRepository.findAll()).thenReturn(Arrays.asList(user1, user2));
        List<User> users = userService.getAllUsers();
        assertEquals(2, users.size());
        verify(userRepository, times(1)).findAll();
    }

    @Test
    void testGetUserById() {
        when(userRepository.findById("1")).thenReturn(Optional.of(user1));
        User foundUser = userService.getUserById("1");
        assertNotNull(foundUser);
        assertEquals("Alice", foundUser.getUsername());
        verify(userRepository, times(1)).findById("1");
    }

    @Test
    void testGetUserByEmail() {
        when(userRepository.findByEmail("alice@example.com")).thenReturn(user1);
        User foundUser = userService.getUserByEmail("alice@example.com");
        assertNotNull(foundUser);
        assertEquals("Alice", foundUser.getUsername());
        verify(userRepository, times(1)).findByEmail("alice@example.com");
    }

    @Test
    void testCreateUser() {
        when(userRepository.save(user1)).thenReturn(user1);
        User created = userService.createUser(user1);
        assertNotNull(created);
        assertEquals("Alice", created.getUsername());
        verify(userRepository, times(1)).save(user1);
    }

    @Test
public void testUpdateUser() {
    // 1. Créer et sauvegarder un utilisateur initial
    User user = new User();
    user.setUsername("maatalli");
    user.setPassword("maatalli");
    user.setEmail("maatalli@gmail.com");
    user = userRepository.save(user);

    // 2. Modifier des champs
    user.setUsername("updatedUsername");
    user.setEmail("updated@example.com");

    // 3. Appeler la méthode à tester
    User updatedUser = userService.updateUser(user);

    // 4. Vérifier que la mise à jour a bien eu lieu
    assertEquals("updatedUsername", updatedUser.getUsername());
    assertEquals("updated@example.com", updatedUser.getEmail());
}


    @Test
    void testDeleteUser() {
        doNothing().when(userRepository).deleteById("1");
        userService.deleteUser("1");
        verify(userRepository, times(1)).deleteById("1");
    }

    @Test
    void testCountUsersByRole() {
        when(userRepository.countByRole(Role.EMPLOYEE)).thenReturn(5L);
        long count = userService.countUsersByRole(Role.EMPLOYEE);
        assertEquals(5L, count);
    }

    @Test
    void testCountSiteSupervisors() {
        when(userRepository.countByRole(Role.SITE_SUPERVISOR)).thenReturn(3L);
        long count = userService.countSiteSupervisors();
        assertEquals(3L, count);
    }

    @Test
    void testGetUsersByRole() {
        when(userRepository.findByRole(String.valueOf(Role.EMPLOYEE))).thenReturn(List.of(user1));
        List<User> employees = userService.getUsersByRole(Role.EMPLOYEE);
        assertEquals(1, employees.size());
        assertEquals("Alice", employees.get(0).getUsername());
    }

}
