package com.example.stage.Repository;


import com.example.stage.Model.Notification;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;


@Repository
public interface NotificationRepository extends MongoRepository<Notification, String> {

    List<Notification> findByIsReadFalse();
//    List<Notification> findByUserIdAndIsReadFalse(String userId);
//    List<Notification> findByUserIdInAndIsReadFalse(List<String> userIds);
    List<Notification> findByRoleAndIsReadFalse(String role);
//
//    // Comptage selon statut + date
//    long countByStatutAndDate(LocalDate date, String statut);
//
//    // Comptage selon statut (toutes dates)
//    long countByStatut(String statut);
@Query(value = "{ 'statut': { $in: ['absence', 'depart_non_autorise'] } }", count = true)
long countAbsenceOrUnauthorizedDepart();
    // Compter les notifications avec statut 'absence' dans une période
    @Query(value = "{ 'statut': 'absence', 'date': { $gte: ?0, $lt: ?1 } }", count = true)
    long countAbsencesByDateRange(LocalDate startDate, LocalDate endDate);

    // Compter les notifications avec statut 'depart_non_autorise' dans une période
    @Query(value = "{ 'statut': 'depart_non_autorise', 'date': { $gte: ?0, $lt: ?1 } }", count = true)
    long countDepartNonAutorisesByDateRange(LocalDate startDate, LocalDate endDate);
    // Comptage pour tous les statuts sur une date
    long countByDate(LocalDate date);

    long countByStatut(String statut);
}
