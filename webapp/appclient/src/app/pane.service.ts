import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class PaneService {

  public mouseInPane: boolean = false
  public showScannerPane: boolean = false

  constructor() { }


  public openScannerPane():void {
    this.showScannerPane = true
  }

}
