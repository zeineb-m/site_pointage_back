package com.example.stage;

import com.example.stage.Model.HeurePointage;
import com.example.stage.Model.Pointage;
import com.example.stage.Model.User;
import com.example.stage.Repository.PointageRepository;
import com.example.stage.Repository.UserRepository;
import com.example.stage.dto.PointageStatsDto;

import com.example.stage.service.PointageServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;

import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class PointageServiceImplTest {

    @Mock
    private PointageRepository pointageRepository;

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private PointageServiceImpl pointageService;

    private Pointage pointageJour;
    private Pointage pointageNuit;

    @BeforeEach
    void setUp() {
        HeurePointage h1 = new HeurePointage();
        h1.setHeure(Date.from(LocalDateTime.of(2024, 1, 1, 8, 0)
                .atZone(ZoneId.systemDefault()).toInstant()));

        HeurePointage h2 = new HeurePointage();
        h2.setHeure(Date.from(LocalDateTime.of(2024, 1, 1, 20, 0)
                .atZone(ZoneId.systemDefault()).toInstant()));

        pointageJour = new Pointage();
        pointageJour.setId("1");
        pointageJour.setArrivees(List.of(h1));

        pointageNuit = new Pointage();
        pointageNuit.setId("2");
        pointageNuit.setArrivees(List.of(h2));
    }

    @Test
    void testGetAllPointages() {
        when(pointageRepository.findAll()).thenReturn(List.of(pointageJour, pointageNuit));
        List<Pointage> pointages = pointageService.getAllPointages();
        assertEquals(2, pointages.size());
        verify(pointageRepository, times(1)).findAll();
    }

    @Test
    void testGetPointageById_Found() {
        when(pointageRepository.findById("1")).thenReturn(Optional.of(pointageJour));
        Pointage result = pointageService.getPointageById("1");
        assertNotNull(result);
        assertEquals("1", result.getId());
    }

    @Test
    void testGetPointageById_NotFound() {
        when(pointageRepository.findById("404")).thenReturn(Optional.empty());
        assertThrows(RuntimeException.class, () -> pointageService.getPointageById("404"));
    }

    @Test
    void testGetStatsJourNuit() {
        when(pointageRepository.findAll()).thenReturn(List.of(pointageJour, pointageNuit));
        PointageStatsDto stats = pointageService.getStatsJourNuit();

        assertEquals(1, stats.getPointagesJour());
        assertEquals(1, stats.getPointagesNuit());
    }

    @Test
    void testGetPointagesBySupervisor() {
        User emp1 = new User();
        emp1.setId("emp1");
        User emp2 = new User();
        emp2.setId("emp2");

        when(userRepository.findBySupervisorId("sup1")).thenReturn(List.of(emp1, emp2));
        when(pointageRepository.findByUserIdInCustom(List.of("emp1", "emp2"))).thenReturn(List.of(pointageJour, pointageNuit));

        List<Pointage> result = pointageService.getPointagesBySupervisor("sup1");

        assertEquals(2, result.size());
        verify(userRepository).findBySupervisorId("sup1");
        verify(pointageRepository).findByUserIdInCustom(List.of("emp1", "emp2"));
    }

    @Test
    void testGetPointagesBySupervisor_Empty() {
        when(userRepository.findBySupervisorId("sup1")).thenReturn(Collections.emptyList());

        List<Pointage> result = pointageService.getPointagesBySupervisor("sup1");

        assertTrue(result.isEmpty());
        verify(pointageRepository, never()).findByUserIdInCustom(any());
    }
}
