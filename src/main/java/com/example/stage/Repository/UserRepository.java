package com.example.stage.Repository;


import com.example.stage.Model.Role;
import com.example.stage.Model.User;
import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface UserRepository extends MongoRepository<User, String> {
    User findByUsername(String username);
     User findByEmail(String email);
    List<User> findBySupervisorId(String supervisorId);

    long countByStatut(String statut);

    long countByRole(Role role);
    List<User> findByRole(String role);
}
