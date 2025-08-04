package com.example.stage.Controller;

import com.example.stage.Repository.NotificationRepository;
import com.example.stage.Repository.PointageRepository;
import com.example.stage.Repository.UserRepository;
import com.example.stage.service.DashboardService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;
@RestController
@RequestMapping("/api/dashboard")
@CrossOrigin(origins = "*")
public class DashboardController {

    @Autowired
    private DashboardService dashboardService;

    @GetMapping("")

    public ResponseEntity<Map<String, Object>> getStats(
            @RequestParam(name = "date", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date
    ) {
        if (date == null) {
            date = LocalDate.now();
        }
        int year = date.getYear();
        int month = date.getMonthValue();

        return ResponseEntity.ok(dashboardService.getDashboardStats(year, month));
    }

}
