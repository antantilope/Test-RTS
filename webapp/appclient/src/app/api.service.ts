
import { Injectable } from '@angular/core';
import { io } from 'socket.io-client';


@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private socket;

  constructor() {
    const url: string = document.location.origin.replace(/^https?/, 'ws');
    console.log("ApiService::constructor connecting to socket server on " + url);
    this.socket = io(url);
  }
}
