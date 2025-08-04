package com.example.stage.Controller;

import com.example.stage.Model.Pointage;
import com.example.stage.dto.PointageStatsDto;
import com.example.stage.service.PointageService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/pointages")
@CrossOrigin(origins = "*")
public class PointageController {

    @Autowired
    private PointageService pointageService;

    @GetMapping
    public List<Pointage> getAllPointages() {
        return pointageService.getAllPointages();
    }

    @GetMapping("/{id}")
    public Pointage getDetails(@PathVariable String id) {
        return pointageService.getPointageById(id);
    }

    @GetMapping("/stats-jour-nuit")
    public PointageStatsDto getStatsJourNuit() {
        return pointageService.getStatsJourNuit();
    }


    @GetMapping("/supervisor/{supervisorId}")
    public List<Pointage> getPointagesBySupervisor(@PathVariable String supervisorId) {
        return pointageService.getPointagesBySupervisor(supervisorId);
    }
}
