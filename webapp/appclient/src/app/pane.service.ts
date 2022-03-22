import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class PaneService {

  public mouseInPane: boolean = false
  public allChatPaneVisible: boolean = false

  constructor(
  ) { }

}
