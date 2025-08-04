package com.example.stage.service;

import com.example.stage.Model.HeurePointage;
import com.example.stage.Model.Pointage;
import com.example.stage.Model.User;
import com.example.stage.Repository.PointageRepository;
import com.example.stage.Repository.UserRepository;
import com.example.stage.dto.PointageStatsDto;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.ZoneId;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
public class PointageServiceImpl implements PointageService {

    @Autowired
    private PointageRepository pointageRepository;
    @Autowired
    private  UserRepository userRepository;

    @Override
    public List<Pointage> getAllPointages() {
        return pointageRepository.findAll();
    }

    @Override
    public Pointage getPointageById(String id) {
        Optional<Pointage> pointage = pointageRepository.findById(id);
        return pointage.orElseThrow(() -> new RuntimeException("Pointage avec ID " + id + " introuvable."));
    }

    @Override
    public PointageStatsDto getStatsJourNuit() {
        List<Pointage> pointages = pointageRepository.findAll();
        int countJour = 0;
        int countNuit = 0;

        LocalTime debutJour = LocalTime.of(7, 30);
        LocalTime finJour = LocalTime.of(17, 30);
        LocalTime debutNuit1 = LocalTime.of(19, 0);
        LocalTime finNuit2 = LocalTime.of(5, 0);

        for (Pointage pointage : pointages) {
            List<HeurePointage> arrivees = pointage.getArrivees();

            if (arrivees != null && !arrivees.isEmpty()) {
                for (HeurePointage arrivee : arrivees) {
                    Date dateHeure = arrivee.getHeure();
                    LocalDateTime heureArrivee = null;

                    if (dateHeure != null) {
                        heureArrivee = dateHeure.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime();
                    }

                    if (heureArrivee != null) {
                        LocalTime time = heureArrivee.toLocalTime();

                        boolean isJour = !time.isBefore(debutJour) && !time.isAfter(finJour);
                        boolean isNuit = (time.equals(debutNuit1) || time.isAfter(debutNuit1)) || time.isBefore(finNuit2);

                        if (isJour) {
                            countJour++;
                        } else if (isNuit) {
                            countNuit++;
                        } else {
                            System.out.println("Arrivée hors plage attendue : " + time + " pointageId=" + pointage.getId());
                        }
                    } else {
                        System.out.println("Arrivée sans heure : pointageId=" + pointage.getId());
                    }
                }
            } else {
                System.out.println("Pointage sans arrivees : id=" + pointage.getId());
            }
        }

        return new PointageStatsDto(countJour, countNuit);
    }
    @Override
    public List<Pointage> getPointagesBySupervisor(String supervisorId) {
        // Étape 1 : récupérer tous les users (employés) sous ce supervisor
        List<User> employees = userRepository.findBySupervisorId(supervisorId);


        List<String> employeeIds = employees.stream()
                .map(User::getId)
                .collect(Collectors.toList());


        if (employeeIds.isEmpty()) {
            return Collections.emptyList();
        }


        return pointageRepository.findByUserIdInCustom(employeeIds);
    }

}