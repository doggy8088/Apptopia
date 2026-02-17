import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { LocationService, ServiceArea, ErrorResponse } from './location.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, CommonModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('我要尿尿');
  protected loading = signal(false);
  protected serviceArea = signal<ServiceArea | null>(null);
  protected error = signal<string | null>(null);

  constructor(private locationService: LocationService) {}

  onFindRestArea() {
    this.loading.set(true);
    this.error.set(null);
    this.serviceArea.set(null);

    this.locationService.getCurrentPosition().subscribe({
      next: (position) => {
        const locationData = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          heading: position.coords.heading ?? 0,
          speed: position.coords.speed ?? 100 // Default to 100 km/h if not available
        };

        this.locationService.findNearestServiceArea(locationData).subscribe({
          next: (area) => {
            this.serviceArea.set(area);
            this.loading.set(false);
          },
          error: (err: ErrorResponse) => {
            this.error.set(err.message);
            this.loading.set(false);
          }
        });
      },
      error: (err: ErrorResponse) => {
        this.error.set(err.message);
        this.loading.set(false);
      }
    });
  }

  openGoogleMaps(area: ServiceArea) {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${area.latitude},${area.longitude}&travelmode=driving`;
    window.open(url, '_blank');
  }
}
