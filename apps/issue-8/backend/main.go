package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math"
	"net/http"
	"os"
	"time"

	"github.com/rs/cors"
)

// ServiceArea represents a highway service area
type ServiceArea struct {
	ID          string  `json:"id"`
	Name        string  `json:"name"`
	Direction   string  `json:"direction"` // 北上 or 南下
	Highway     string  `json:"highway"`   // 國道1號, 國道3號, etc.
	Latitude    float64 `json:"latitude"`
	Longitude   float64 `json:"longitude"`
	Mileage     float64 `json:"mileage"` // 公里數
	Distance    float64 `json:"distance,omitempty"`
	ETA         string  `json:"eta,omitempty"`
	ParkingInfo *ParkingInfo `json:"parkingInfo,omitempty"`
}

// ParkingInfo represents parking availability status
type ParkingInfo struct {
	Status          string `json:"status"`          // 充足, 稍滿, 已滿
	AvailableSpaces int    `json:"availableSpaces"`
	TotalSpaces     int    `json:"totalSpaces"`
	ColorCode       string `json:"colorCode"` // #28a745 (green), #ffc107 (yellow), #dc3545 (red)
}

// LocationRequest represents user's location and movement data
type LocationRequest struct {
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`
	Heading   float64 `json:"heading"` // 0-360 degrees, 0 = North
	Speed     float64 `json:"speed"`   // km/h
}

// ErrorResponse represents API error response
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
}

var (
	// Mock service areas data (to be replaced with TDX API)
	serviceAreas = []ServiceArea{
		{
			ID:        "1",
			Name:      "湖口服務區",
			Direction: "北上",
			Highway:   "國道1號",
			Latitude:  24.9051,
			Longitude: 121.0398,
			Mileage:   97.0,
		},
		{
			ID:        "2",
			Name:      "湖口服務區",
			Direction: "南下",
			Highway:   "國道1號",
			Latitude:  24.9051,
			Longitude: 121.0398,
			Mileage:   97.0,
		},
		{
			ID:        "3",
			Name:      "西螺服務區",
			Direction: "北上",
			Highway:   "國道1號",
			Latitude:  23.7951,
			Longitude: 120.4698,
			Mileage:   233.0,
		},
	}
)

func main() {
	mux := http.NewServeMux()
	
	// Health check endpoint
	mux.HandleFunc("/api/health", healthHandler)
	
	// Main endpoint to find nearest service area
	mux.HandleFunc("/api/nearest-service-area", nearestServiceAreaHandler)
	
	// CORS middleware
	handler := cors.New(cors.Options{
		AllowedOrigins:   []string{"http://localhost:4200", "http://localhost:8080"},
		AllowedMethods:   []string{"GET", "POST", "OPTIONS"},
		AllowedHeaders:   []string{"Content-Type", "Authorization"},
		AllowCredentials: true,
	}).Handler(mux)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Server starting on port %s\n", port)
	log.Fatal(http.ListenAndServe(":"+port, handler))
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status": "healthy",
		"time":   time.Now().Format(time.RFC3339),
	})
}

func nearestServiceAreaHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	
	if r.Method != http.MethodPost {
		w.WriteHeader(http.StatusMethodNotAllowed)
		json.NewEncoder(w).Encode(ErrorResponse{
			Error:   "method_not_allowed",
			Message: "只接受 POST 請求",
		})
		return
	}

	var req LocationRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(ErrorResponse{
			Error:   "invalid_request",
			Message: "無法解析請求內容",
		})
		return
	}

	// Validate coordinates
	if req.Latitude < 20 || req.Latitude > 26 || req.Longitude < 118 || req.Longitude > 123 {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(ErrorResponse{
			Error:   "out_of_bounds",
			Message: "偵測到您目前不在高速公路上，本功能僅限國道急尿使用。",
		})
		return
	}

	// Find nearest service area based on direction
	nearest := findNearestServiceArea(req)
	if nearest == nil {
		w.WriteHeader(http.StatusNotFound)
		json.NewEncoder(w).Encode(ErrorResponse{
			Error:   "no_service_area_found",
			Message: "找不到附近的服務區或休息站",
		})
		return
	}

	// Add mock parking info
	nearest.ParkingInfo = getMockParkingInfo()

	json.NewEncoder(w).Encode(nearest)
}

func findNearestServiceArea(req LocationRequest) *ServiceArea {
	var nearest *ServiceArea
	minDistance := 999999.0

	// Determine direction based on heading (simplified logic)
	// 0-90 or 270-360 = 北上, 90-270 = 南下
	direction := "北上"
	if req.Heading > 90 && req.Heading < 270 {
		direction = "南下"
	}

	for i := range serviceAreas {
		area := &serviceAreas[i]
		
		// Filter by direction
		if area.Direction != direction {
			continue
		}

		// Calculate distance using Haversine formula
		dist := haversineDistance(req.Latitude, req.Longitude, area.Latitude, area.Longitude)
		
		if dist < minDistance {
			minDistance = dist
			nearest = area
		}
	}

	if nearest != nil {
		// Calculate ETA based on distance and speed
		nearest.Distance = minDistance
		if req.Speed > 0 {
			etaMinutes := (minDistance / req.Speed) * 60
			nearest.ETA = fmt.Sprintf("%.0f 分鐘", etaMinutes)
		} else {
			nearest.ETA = "計算中..."
		}
	}

	return nearest
}

// haversineDistance calculates the distance between two lat/lng points in kilometers
func haversineDistance(lat1, lon1, lat2, lon2 float64) float64 {
	const R = 6371.0 // Earth radius in kilometers
	
	lat1Rad := lat1 * math.Pi / 180
	lat2Rad := lat2 * math.Pi / 180
	deltaLat := (lat2 - lat1) * math.Pi / 180
	deltaLon := (lon2 - lon1) * math.Pi / 180

	a := math.Sin(deltaLat/2)*math.Sin(deltaLat/2) +
		math.Cos(lat1Rad)*math.Cos(lat2Rad)*
			math.Sin(deltaLon/2)*math.Sin(deltaLon/2)

	c := 2 * math.Atan2(math.Sqrt(a), math.Sqrt(1-a))

	return R * c
}

func getMockParkingInfo() *ParkingInfo {
	// Mock data - to be replaced with TDX API
	available := 128
	total := 200
	ratio := float64(available) / float64(total)

	status := "已滿"
	colorCode := "#dc3545" // red

	if ratio > 0.5 {
		status = "充足"
		colorCode = "#28a745" // green
	} else if ratio >= 0.2 {
		status = "稍滿"
		colorCode = "#ffc107" // yellow
	}

	return &ParkingInfo{
		Status:          status,
		AvailableSpaces: available,
		TotalSpaces:     total,
		ColorCode:       colorCode,
	}
}
