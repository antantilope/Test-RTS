
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { HttpClientModule, HttpClientXsrfModule } from '@angular/common/http';
import { AngularDraggableModule } from 'angular2-draggable';


import { AppComponent } from './app.component';
import { TakeoverComponent } from './takeover/takeover.component';
import { GamedisplayComponent } from './gamedisplay/gamedisplay.component';
import { AllchatComponent } from './allchat/allchat.component';
import { MainmenuComponent } from './mainmenu/mainmenu.component';
import { ShippaneComponent } from './shippane/shippane.component';
import { EngpaneComponent } from './engpane/engpane.component';
import { UpgradepaneComponent } from './upgradepane/upgradepane.component';


@NgModule({
  declarations: [
    AppComponent,
    TakeoverComponent,
    GamedisplayComponent,
    AllchatComponent,
    MainmenuComponent,
    ShippaneComponent,
    EngpaneComponent,
    UpgradepaneComponent,
  ],
  imports: [
    BrowserModule,
    AngularDraggableModule,
    FormsModule,
    HttpClientModule,
    HttpClientXsrfModule.withOptions({
      cookieName: 'csrftoken',
      headerName: 'csrf-token',
    }),
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
