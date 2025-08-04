package com.example.stage.service;

import com.example.stage.Model.Message;
import com.example.stage.Model.User;
import com.example.stage.Repository.MessageRepository;
import com.example.stage.Repository.UserRepository;
import com.example.stage.dto.MessageDTO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Date;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class MessageServiceImpl implements MessageService {

    @Autowired
    private MessageRepository messageRepository;

    @Autowired
    private UserRepository userRepository;

    /**
     * Envoie un message, avec horodatage et statut de lecture.
     */
    @Override
    public Message sendMessage(Message message) {
        message.setTimestamp(new Date());
        message.setRead(false);
        return messageRepository.save(message);
    }

    /**
     * Récupère la conversation entre deux utilisateurs (HR et superviseur).
     */
    @Override
    public List<MessageDTO> getConversation(String user1Id, String user2Id) {
        List<Message> messages = messageRepository.findConversation(user1Id, user2Id);

        // Récupérer les utilisateurs pour enrichir les données
        User user1 = userRepository.findById(user1Id).orElse(null);
        User user2 = userRepository.findById(user2Id).orElse(null);

        return messages.stream().map(msg -> {
            MessageDTO dto = new MessageDTO();
            dto.setId(msg.getId());
            dto.setSenderId(msg.getSenderId());
            dto.setReceiverId(msg.getReceiverId());
            dto.setContent(msg.getContent());
            dto.setTimestamp(msg.getTimestamp());
            dto.setRead(msg.isRead());

            // Déduire les noms et rôles
            if (user1 != null && msg.getSenderId().equals(user1.getId())) {
                dto.setSenderUsername(user1.getUsername());
                dto.setSenderRole(user1.getRole() != null ? user1.getRole().name() : "");
            } else if (user2 != null && msg.getSenderId().equals(user2.getId())) {
                dto.setSenderUsername(user2.getUsername());
                dto.setSenderRole(user2.getRole() != null ? user2.getRole().name() : "");
            }

            if (user1 != null && msg.getReceiverId().equals(user1.getId())) {
                dto.setReceiverUsername(user1.getUsername());
                dto.setReceiverRole(user1.getRole() != null ? user1.getRole().name() : "");
            } else if (user2 != null && msg.getReceiverId().equals(user2.getId())) {
                dto.setReceiverUsername(user2.getUsername());
                dto.setReceiverRole(user2.getRole() != null ? user2.getRole().name() : "");
            }

            return dto;
        }).collect(Collectors.toList());
    }

    /**
     * Récupère les messages reçus par un utilisateur (boîte de réception).
     */
    @Override
    public List<MessageDTO> getReceivedMessages(String receiverId) {
        List<Message> messages = messageRepository.findByReceiverIdOrderByTimestampAsc(receiverId);

        return messages.stream().map(msg -> {
            User sender = userRepository.findById(msg.getSenderId()).orElse(null);
            User receiver = userRepository.findById(msg.getReceiverId()).orElse(null);

            MessageDTO dto = new MessageDTO();
            dto.setId(msg.getId());
            dto.setSenderId(msg.getSenderId());
            dto.setReceiverId(msg.getReceiverId());
            dto.setContent(msg.getContent());
            dto.setTimestamp(msg.getTimestamp());
            dto.setRead(msg.isRead());

            dto.setSenderUsername(sender != null ? sender.getUsername() : "Inconnu");
            dto.setSenderRole(sender != null && sender.getRole() != null ? sender.getRole().name() : "");

            dto.setReceiverUsername(receiver != null ? receiver.getUsername() : "Inconnu");
            dto.setReceiverRole(receiver != null && receiver.getRole() != null ? receiver.getRole().name() : "");

            return dto;
        }).collect(Collectors.toList());
    }

}
