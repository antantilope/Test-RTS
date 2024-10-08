import { Injectable } from '@angular/core';
import { Subject } from 'rxjs'

@Injectable({
  providedIn: 'root'
})
export class PaneService {

  public PANE_ALL_CHAT = "all-chat"
  public PANE_MAIN_MENU = "main-menu"
  public PANE_SHIP = "ship-menu"
  public PANE_SCANNER = "scanner-display"

  public lastShipPaneSubPane: string

  public allChatPaneVisible: boolean = false
  public mainMenuPaneVisible: boolean = false
  public shipPaneVisible: boolean = false
  public scannerPaneVisible: boolean = false

  private zIndexes: string[] = []
  public zIndexesUpdated: Subject<string[]> = new Subject()

  // Array of panes that the mouse is currently inside of.
  private _mouseInPane: string[] = []

  private inputIsFocused = false

  constructor(
  ) {
    this.zIndexes = [
      this.PANE_ALL_CHAT,
      this.PANE_MAIN_MENU,
      this.PANE_SHIP,
      this.PANE_SCANNER,
    ]
  }

  setInputIsFocused(value: boolean, from: string) {
    this.inputIsFocused = value
  }

  getInputIsFocused() {
    return this.inputIsFocused
  }

  openAllchatPane() {
    this.allChatPaneVisible = true
    this.shipPaneVisible = false
    this.scannerPaneVisible = false
    this.mainMenuPaneVisible = false
    this._mouseInPane = this._mouseInPane.filter(pn => pn == this.PANE_ALL_CHAT)
  }
  closeAllchatPane() {
    this.allChatPaneVisible = false
    this._mouseInPane = this._mouseInPane.filter(pn => pn != this.PANE_ALL_CHAT)
  }

  openMainMenuPane() {
    this.mainMenuPaneVisible = true
    this.allChatPaneVisible = false
    this.shipPaneVisible = false
    this.scannerPaneVisible = false
    this._mouseInPane = this._mouseInPane.filter(pn => pn == this.PANE_MAIN_MENU)
  }
  closeMainMenuPane() {
    this.mainMenuPaneVisible = false
    this._mouseInPane = this._mouseInPane.filter(pn => pn != this.PANE_MAIN_MENU)
  }

  openShipMenuPane() {
    this.shipPaneVisible = true
    this.mainMenuPaneVisible = false
    this.allChatPaneVisible = false
    this.scannerPaneVisible = false
    this._mouseInPane = this._mouseInPane.filter(pn => pn == this.PANE_SHIP)
  }
  closeShipMenuPane() {
    this.shipPaneVisible = false
    this._mouseInPane = this._mouseInPane.filter(pn => pn != this.PANE_SHIP)
  }

  openScannerPane() {
    this.scannerPaneVisible = true
    this.shipPaneVisible = false
    this.mainMenuPaneVisible = false
    this.allChatPaneVisible = false
    this._mouseInPane = this._mouseInPane.filter(pn => pn == this.PANE_SCANNER)
  }
  closeScannerPane() {
    this.scannerPaneVisible = false
    this._mouseInPane = this._mouseInPane.filter(pn => pn != this.PANE_SCANNER)
  }


  mouseInPane(): boolean {
    return this._mouseInPane.length > 0
  }

  mouseInScannerPane(): boolean {
    return this._mouseInPane.indexOf(this.PANE_SCANNER) != -1
  }

  addToTopOfZIndexes(paneName: string) {
    const currentIndex = this.zIndexes.indexOf(paneName)
    if(currentIndex === -1) {
      return console.warn("cannot find paneName " + paneName)
    }
    this.zIndexes.splice(currentIndex, 1)
    this.zIndexes.push(paneName)
    this.zIndexesUpdated.next(this.zIndexes)
  }

  getZIndex(paneName: string): number {
    const currentIndex = this.zIndexes.indexOf(paneName)
    if(currentIndex === -1) {
      throw new Error("cannot find paneName " + paneName)
    }
    return currentIndex
  }

  registerMouseEnteringPane(paneName: string) {
    if(this._mouseInPane.indexOf(paneName) === -1) {
      this._mouseInPane.push(paneName)
    }
  }

  registerMouseLeavingPane(paneName: string) {
    this._mouseInPane = this._mouseInPane.filter(pn => pn !== paneName)
  }

}
