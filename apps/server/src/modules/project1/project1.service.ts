import { Injectable } from '@nestjs/common';
import type { ApiResponse, HelloData } from '@app/shared';

@Injectable()
export class Project1Service {
  hello(): ApiResponse<HelloData> {
    return {
      code: 0,
      message: 'ok',
      data: { project: 'project1', time: new Date().toISOString() },
    };
  }
}
