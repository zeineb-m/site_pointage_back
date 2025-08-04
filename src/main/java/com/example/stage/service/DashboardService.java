package com.example.stage.service;

import com.example.stage.Model.Pointage;
import com.example.stage.Repository.NotificationRepository;
import com.example.stage.Repository.PointageRepository;
import com.example.stage.Repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalTime;
import java.time.YearMonth;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
@Service
public class DashboardService {

    @Autowired
    private PointageRepository pointageRepository;

    @Autowired
    private NotificationRepository notificationRepository;

    @Autowired
    private UserRepository userRepository;
    public Map<String, Object> getDashboardStats(int year, int month) {
        Map<String, Object> stats = new HashMap<>();

        long totalEmployees = userRepository.count();
        System.out.println("👥 Total employés : " + totalEmployees);

        // Calculer la période du mois
        YearMonth ym = YearMonth.of(year, month);
        LocalDate startDate = ym.atDay(1);
        LocalDate endDate = ym.plusMonths(1).atDay(1);

        // Compter absences et départs non autorisés dans ce mois
        long totalAbsences = notificationRepository.countAbsencesByDateRange(startDate, endDate);
        System.out.println("❌ Absences : " + totalAbsences);

        long totalDepartNonAutorise = notificationRepository.countDepartNonAutorisesByDateRange(startDate, endDate);
        System.out.println("🚫 Départs non autorisés : " + totalDepartNonAutorise);

        // Pointages dans le mois
        int daysInMonth = ym.lengthOfMonth();
        long presenceCount = pointageRepository.countByDatePointageBetween(startDate, endDate);
        System.out.println("Présences dans le mois : " + presenceCount);

        double tauxPresence = (totalEmployees == 0 || daysInMonth == 0) ? 0.0
                : (presenceCount * 100.0) / (totalEmployees * daysInMonth);

        System.out.println("✅ Taux de présence mensuel : " + tauxPresence + " %");

        stats.put("totalEmployees", totalEmployees);
        stats.put("absences", totalAbsences);
        stats.put("departNonAutorise", totalDepartNonAutorise);
        stats.put("tauxPresence", tauxPresence);

        return stats;
    }

}
