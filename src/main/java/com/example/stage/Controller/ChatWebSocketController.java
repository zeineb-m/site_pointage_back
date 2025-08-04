package com.example.stage.Controller;

import com.example.stage.Model.Message;
import com.example.stage.Repository.MessageRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.RestController;

import java.util.Date;

@RestController
@CrossOrigin(origins = "*")
public class ChatWebSocketController {

    @Autowired
    private SimpMessagingTemplate messagingTemplate;

    @Autowired
    private MessageRepository messageRepository;

    @MessageMapping("/chat") // préfixe "/app/chat"
    public void processMessage(Message message) {
        message.setTimestamp(new Date());
        message.setRead(false);

        // Sauvegarde MongoDB
        messageRepository.save(message);

        // Envoi en temps réel au destinataire
        messagingTemplate.convertAndSend(
                "/topic/messages/" + message.getReceiverId(),
                message
        );
    }
}
