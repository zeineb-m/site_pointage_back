package com.example.stage.Repository;



import com.example.stage.Model.Pointage;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;

import java.time.LocalDate;
import java.util.List;

public interface PointageRepository extends MongoRepository<Pointage, String> {

    long count();

//
//    long countByStatut(String statut);
//
//    long countByDatePointage(LocalDate date);
//
//
//    long countByStatutAndDatePointage(String statut, LocalDate date);


    List<Pointage> findByDatePointage(LocalDate date);
    @Query(value = "{ 'date_pointage': { $gte: ?0, $lt: ?1 } }", count = true)
    long countByDatePointageBetween(LocalDate startDate, LocalDate endDate);
    @Query("{ 'user_id': { $in: ?0 } }")
    List<Pointage> findByUserIdInCustom(List<String> userIds);

//    @Query(value = "{ 'statut': ?0 }", count = true)
//    long countByCustomStatut(String statut);
//
//
//    @Query("{ 'statut': 'depart_non_autorise' }")
//    long countUnauthorizedDepartures();
}