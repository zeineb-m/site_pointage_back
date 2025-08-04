package com.example.stage.Controller;

import com.example.stage.Model.Message;
import com.example.stage.Repository.MessageRepository;
import com.example.stage.dto.MessageDTO;
import com.example.stage.service.MessageService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/messages")
@CrossOrigin(origins = "*")
public class MessageController {

    @Autowired
    private MessageService messageService;
    @Autowired
    private MessageRepository messageRepository;

    @PostMapping("/send")
    public ResponseEntity<Message> sendMessage(@RequestBody Message message) {
        return ResponseEntity.ok(messageService.sendMessage(message));
    }

    @GetMapping("/conversation")
    public ResponseEntity<List<MessageDTO>> getConversation(
            @RequestParam String user1Id,
            @RequestParam String user2Id
    ) {
        List<MessageDTO> conversation = messageService.getConversation(user1Id, user2Id);
        return ResponseEntity.ok(conversation);
    }

    @GetMapping("/received")
    public List<MessageDTO> getReceivedMessages(@RequestParam String receiverId) {
        return messageService.getReceivedMessages(receiverId);
    }
    @PutMapping("/{id}/read")
    public ResponseEntity<?> markMessageAsRead(@PathVariable String id) {
        Optional<Message> optMsg = messageRepository.findById(id);
        if (optMsg.isPresent()) {
            Message msg = optMsg.get();
            msg.setRead(true);
            messageRepository.save(msg);
            return ResponseEntity.ok().build();
        }
        return ResponseEntity.notFound().build();
    }

}
