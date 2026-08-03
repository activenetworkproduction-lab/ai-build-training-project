import { Module } from '@nestjs/common';
import { Project2Controller } from './project2.controller';
import { Project2Service } from './project2.service';

@Module({
  controllers: [Project2Controller],
  providers: [Project2Service],
})
export class Project2Module {}
