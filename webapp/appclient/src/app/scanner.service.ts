import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ScannerService {

  public scannerTargetIDCursor: string | null = null

  constructor() { }
}
