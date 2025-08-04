package com.example.stage.dto;
public class PointageStatsDto {
    private int pointagesJour;
    private int pointagesNuit;

    public PointageStatsDto(int pointagesJour, int pointagesNuit) {
        this.pointagesJour = pointagesJour;
        this.pointagesNuit = pointagesNuit;
    }

    public int getPointagesJour() { return pointagesJour; }
    public void setPointagesJour(int pointagesJour) { this.pointagesJour = pointagesJour; }
    public int getPointagesNuit() { return pointagesNuit; }
    public void setPointagesNuit(int pointagesNuit) { this.pointagesNuit = pointagesNuit; }
}