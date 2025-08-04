package com.example.stage.service;

import com.example.stage.Model.Message;
import com.example.stage.dto.MessageDTO;

import java.util.List;

public interface MessageService {
    Message sendMessage(Message message);
    public List<MessageDTO> getConversation(String user1Id, String user2Id) ;
    public List<MessageDTO> getReceivedMessages(String receiverId) ;

}
