package com.example.stage.Repository;

import com.example.stage.Model.Message;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface MessageRepository extends MongoRepository<Message, String> {

    List<Message> findByReceiverId(String receiverId);
    // Renvoie les messages entre deux utilisateurs, peu importe qui est l’expéditeur
    @Query("{$or:[{senderId:?0, receiverId:?1}, {senderId:?1, receiverId:?0}]}")
    List<Message> findConversation(String user1Id, String user2Id);

    @Query("{$or: [ " +
            "{ $and: [ { senderId: ?0 }, { receiverId: ?1 } ] }, " +
            "{ $and: [ { senderId: ?1 }, { receiverId: ?0 } ] } " +
            "] }")
    List<Message> findBySenderAndReceiver(String senderId, String receiverId);

    List<Message> findByReceiverIdOrderByTimestampAsc(String receiverId);
    List<Message> findBySenderIdAndReceiverIdOrReceiverIdAndSenderId(
            String senderId1, String receiverId1, String senderId2, String receiverId2);
}