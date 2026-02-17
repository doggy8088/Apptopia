import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, from, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

export interface LocationRequest {
  latitude: number;
  longitude: number;
  heading: number;
  speed: number;
}

export interface ParkingInfo {
  status: string;
  availableSpaces: number;
  totalSpaces: number;
  colorCode: string;
}

export interface ServiceArea {
  id: string;
  name: string;
  direction: string;
  highway: string;
  latitude: number;
  longitude: number;
  mileage: number;
  distance?: number;
  eta?: string;
  parkingInfo?: ParkingInfo;
}

export interface ErrorResponse {
  error: string;
  message: string;
}

export interface GeolocationPosition {
  coords: {
    latitude: number;
    longitude: number;
    accuracy: number;
    heading: number | null;
    speed: number | null;
  };
  timestamp: number;
}

@Injectable({
  providedIn: 'root'
})
export class LocationService {
  private readonly apiUrl = 'http://localhost:8080/api';

  constructor(private http: HttpClient) {}

  getCurrentPosition(): Observable<GeolocationPosition> {
    return new Observable((observer) => {
      if (!navigator.geolocation) {
        observer.error({
          error: 'geolocation_not_supported',
          message: '您的瀏覽器不支援定位功能'
        });
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          observer.next(position as GeolocationPosition);
          observer.complete();
        },
        (error) => {
          let errorMessage = '無法取得您的位置';
          switch (error.code) {
            case error.PERMISSION_DENIED:
              errorMessage = '哎呀！沒拿到 GPS 權限，我不知道你在哪條高速公路上。';
              break;
            case error.POSITION_UNAVAILABLE:
              errorMessage = 'GPS 訊號不佳，請稍後再試';
              break;
            case error.TIMEOUT:
              errorMessage = '定位請求超時，請重試';
              break;
          }
          observer.error({
            error: 'geolocation_error',
            message: errorMessage
          });
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      );
    });
  }

  findNearestServiceArea(locationData: LocationRequest): Observable<ServiceArea> {
    return this.http.post<ServiceArea>(
      `${this.apiUrl}/nearest-service-area`,
      locationData
    ).pipe(
      catchError(error => {
        if (error.error && error.error.message) {
          return throwError(() => error.error);
        }
        return throwError(() => ({
          error: 'server_error',
          message: '路況資料庫連線中斷，請先觀察路邊里程牌。'
        }));
      })
    );
  }
}
