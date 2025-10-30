import { Component, signal } from '@angular/core';
import {RouterOutlet, Router} from '@angular/router';
import * as THREE from 'three';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  protected readonly title = signal('Agents');
  constructor(private router: Router){

  }

  redirectToFormsButton() {
    this.router.navigate(['/test']);   
  } 
}
  

