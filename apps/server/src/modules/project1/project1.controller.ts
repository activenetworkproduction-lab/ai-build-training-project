import { Controller, Get } from '@nestjs/common';
import type { ApiResponse, HelloData } from '@app/shared';
import { Project1Service } from './project1.service';

@Controller()
export class Project1Controller {
  constructor(private readonly service: Project1Service) {}

  // GET /api/project1/hello
  @Get('hello')
  hello(): ApiResponse<HelloData> {
    return this.service.hello();
  }
}
