import { Controller, Get } from '@nestjs/common';
import type { ApiResponse, HelloData } from '@app/shared';
import { Project2Service } from './project2.service';

@Controller()
export class Project2Controller {
  constructor(private readonly service: Project2Service) {}

  // GET /api/project2/hello
  @Get('hello')
  hello(): ApiResponse<HelloData> {
    return this.service.hello();
  }
}
