import subprocess
import sys
import time


def run(cmd, check=True):
    print(f">>> Executando: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        print(f"❌ Comando falhou: {cmd}")
        sys.exit(result.returncode)
    return result.returncode


def wait_for_db_health(container, timeout=60):
    print(f"⏳ Esperando o container '{container}' ficar healthy...")
    start = time.time()
    while True:
        cmd = f"docker inspect --format='{{{{.State.Health.Status}}}}' {container}"
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        status = result.stdout.strip()

        if "healthy" in status:
            print("✅ Container está healthy!")
            break

        if time.time() - start > timeout:
            print(
                f"⏰ Timeout após {timeout} segundos esperando o container ficar healthy."
            )
            sys.exit(1)

        print(
            f"... Status atual: {status or '[vazio]'} — tentando de novo em 1s"
        )
        time.sleep(1)


def main():
    run("docker compose -f docker-tests.yml -f docker-redis.yml down -v")
    run("docker compose -f docker-tests.yml -f docker-redis.yml up -d")
    wait_for_db_health("test-postgres")

    exit_code = run("pytest tests/", check=False)

    print("🧹 Finalizando containers...")
    run("docker compose -f docker-tests.yml -f docker-redis.yml down -v")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
