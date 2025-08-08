package com.example.stage;

import com.example.stage.Model.Message;
import com.example.stage.Model.User;
import com.example.stage.Model.Role;
import com.example.stage.Repository.MessageRepository;
import com.example.stage.Repository.UserRepository;
import com.example.stage.dto.MessageDTO;
import com.example.stage.service.MessageServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.util.Arrays;
import java.util.Date;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class MessageServiceImplTest {

    @Mock
    private MessageRepository messageRepository;

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private MessageServiceImpl messageService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    void sendMessage_shouldSetDateAndReadFalseAndSave() {
        Message msg = new Message();
        msg.setContent("Hello");

        when(messageRepository.save(any(Message.class))).thenAnswer(invocation -> invocation.getArgument(0));

        Message result = messageService.sendMessage(msg);

        assertNotNull(result.getTimestamp(), "La date doit être définie");
        assertFalse(result.isRead(), "Le message doit être non lu par défaut");
        verify(messageRepository, times(1)).save(msg);
    }

    @Test
    void getConversation_shouldReturnMappedDTOs() {
        // Arrange
        String user1Id = "u1";
        String user2Id = "u2";

        Message m1 = new Message(
                "1",
                user1Id, "User1", "HR",
                user2Id, "User2", "SUPERVISEUR",
                "Salut",
                new Date(),
                false
        );

        Message m2 = new Message(
                "2",
                user2Id, "User2", "SUPERVISEUR",
                user1Id, "User1", "HR",
                "Bonjour",
                new Date(),
                true
        );

        User user1 = new User();
        user1.setId(user1Id);
        user1.setUsername("User1");
        user1.setRole(Role.HR);

        User user2 = new User();
        user2.setId(user2Id);
        user2.setUsername("User2");
        user2.setRole(Role.SITE_SUPERVISOR);

        when(messageRepository.findConversation(user1Id, user2Id)).thenReturn(Arrays.asList(m1, m2));
        when(userRepository.findById(user1Id)).thenReturn(Optional.of(user1));
        when(userRepository.findById(user2Id)).thenReturn(Optional.of(user2));

        // Act
        List<MessageDTO> result = messageService.getConversation(user1Id, user2Id);

        // Assert
        assertEquals(2, result.size());
        assertEquals("User1", result.get(0).getSenderUsername());
        assertEquals("HR", result.get(0).getSenderRole());
        assertEquals("User2", result.get(0).getReceiverUsername());
        assertEquals("SUPERVISEUR", result.get(0).getReceiverRole());

        assertEquals("User2", result.get(1).getSenderUsername());
        assertEquals("SUPERVISEUR", result.get(1).getSenderRole());
        assertEquals("User1", result.get(1).getReceiverUsername());
        assertEquals("HR", result.get(1).getReceiverRole());

        verify(messageRepository, times(1)).findConversation(user1Id, user2Id);
    }

    @Test
    void getReceivedMessages_shouldReturnMappedDTOs() {
        // Arrange
        String receiverId = "u2";

        Message m1 = new Message(
                "1",
                "u1", "Sender", "HR",
                receiverId, "Receiver", "SUPERVISEUR",
                "Hello",
                new Date(),
                false
        );

        User sender = new User();
        sender.setId("u1");
        sender.setUsername("Sender");
        sender.setRole(Role.HR);

        User receiver = new User();
        receiver.setId(receiverId);
        receiver.setUsername("Receiver");
        receiver.setRole(Role.SITE_SUPERVISOR);

        when(messageRepository.findByReceiverIdOrderByTimestampAsc(receiverId)).thenReturn(List.of(m1));
        when(userRepository.findById("u1")).thenReturn(Optional.of(sender));
        when(userRepository.findById(receiverId)).thenReturn(Optional.of(receiver));

        // Act
        List<MessageDTO> result = messageService.getReceivedMessages(receiverId);

        // Assert
        assertEquals(1, result.size());
        MessageDTO dto = result.get(0);
        assertEquals("Sender", dto.getSenderUsername());
        assertEquals("HR", dto.getSenderRole());
        assertEquals("Receiver", dto.getReceiverUsername());
        assertEquals("SUPERVISEUR", dto.getReceiverRole());
        assertEquals("Hello", dto.getContent());

        verify(messageRepository, times(1)).findByReceiverIdOrderByTimestampAsc(receiverId);
    }
}
