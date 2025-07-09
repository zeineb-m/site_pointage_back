package com.example.stage.Controller;


import com.example.stage.Model.Pointage;
import com.example.stage.Repository.PointageRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/pointages")
@CrossOrigin(origins = "*")
public class PointageController {

    @Autowired
    private PointageRepository pointageRepository;

    @GetMapping
    public List<Pointage> getAllPointages() {
        return pointageRepository.findAll();
    }


}
