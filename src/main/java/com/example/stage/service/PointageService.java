package com.example.stage.service;

import com.example.stage.Model.Pointage;
import com.example.stage.dto.PointageStatsDto;

import java.util.List;

public interface PointageService {
    List<Pointage> getAllPointages();
    Pointage getPointageById(String id);
    PointageStatsDto getStatsJourNuit();
    public List<Pointage> getPointagesBySupervisor(String supervisorId);
}
