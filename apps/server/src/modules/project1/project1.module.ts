import { Module } from '@nestjs/common';
import { Project1Controller } from './project1.controller';
import { Project1Service } from './project1.service';

@Module({
  controllers: [Project1Controller],
  providers: [Project1Service],
})
export class Project1Module {}
