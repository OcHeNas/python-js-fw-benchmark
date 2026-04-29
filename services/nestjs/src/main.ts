import "reflect-metadata";
import { Module, Controller, Get } from "@nestjs/common";
import { NestFactory } from "@nestjs/core";

@Controller()
export class AppController {
  @Get("ping")
  ping() {
    return { status: "ok" };
  }

  @Get("items")
  items() {
    return { items: Array.from({ length: 100 }, (_, i) => i) };
  }

  @Get("io")
  async io() {
    await new Promise((resolve) => setTimeout(resolve, 10));
    return { status: "ok" };
  }
}

@Module({
  controllers: [AppController],
})
class AppModule {}

async function bootstrap() {
  const app = await NestFactory.create(AppModule, { logger: false });
  await app.listen(Number(process.env.SERVICE_PORT || 8000), "0.0.0.0");
}

void bootstrap();
