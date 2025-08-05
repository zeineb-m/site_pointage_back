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
void testUpdateUser() {
    when(userRepository.findById("686b8b80fc2de5e429828e0a")).thenReturn(Optional.of(user2));
    when(userRepository.save(user2)).thenReturn(user2);

    User updated = userService.updateUser(user2);
    assertEquals("Bob", updated.getUsername());

    verify(userRepository).findById("2");
    verify(userRepository).save(user2);
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
