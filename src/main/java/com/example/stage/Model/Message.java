package com.example.stage.Model;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.util.Date;

@Document(collection = "message")
public class Message {
    @Id
    private String id;

    private String senderId;
    private String senderUsername;
    private String senderRole;

    private String receiverId;
    private String receiverUsername;
    private String receiverRole;

    private String content;
    private Date timestamp = new Date();
    private boolean read = false;
    public Message() {}


    public Message(String id, String senderId, String senderUsername, String senderRole, String receiverId, String receiverUsername, String receiverRole, String content, Date timestamp, boolean read) {
        this.id = id;
        this.senderId = senderId;
        this.senderUsername = senderUsername;
        this.senderRole = senderRole;
        this.receiverId = receiverId;
        this.receiverUsername = receiverUsername;
        this.receiverRole = receiverRole;
        this.content = content;
        this.timestamp = timestamp;
        this.read = read;
    }

    public String getSenderUsername() {
        return senderUsername;
    }

    public void setSenderUsername(String senderUsername) {
        this.senderUsername = senderUsername;
    }

    public String getReceiverUsername() {
        return receiverUsername;
    }

    public void setReceiverUsername(String receiverUsername) {
        this.receiverUsername = receiverUsername;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getSenderId() {
        return senderId;
    }

    public void setSenderId(String senderId) {
        this.senderId = senderId;
    }

    public String getSenderRole() {
        return senderRole;
    }

    public void setSenderRole(String senderRole) {
        this.senderRole = senderRole;
    }

    public String getReceiverId() {
        return receiverId;
    }

    public void setReceiverId(String receiverId) {
        this.receiverId = receiverId;
    }

    public String getReceiverRole() {
        return receiverRole;
    }

    public void setReceiverRole(String receiverRole) {
        this.receiverRole = receiverRole;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public Date getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Date timestamp) {
        this.timestamp = timestamp;
    }

    public boolean isRead() {
        return read;
    }

    public void setRead(boolean read) {
        this.read = read;
    }
}
