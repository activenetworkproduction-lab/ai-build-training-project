import { Injectable } from '@nestjs/common';
import type { ApiResponse, HelloData } from '@app/shared';

@Injectable()
export class Project2Service {
  hello(): ApiResponse<HelloData> {
    return {
      code: 0,
      message: 'ok',
      data: { project: 'project2', time: new Date().toISOString() },
    };
  }
}
