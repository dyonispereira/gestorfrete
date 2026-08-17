"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Truck } from "lucide-react";

import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Input, Label } from "@gestorfrete/ui";

import { useAuth } from "@/core/auth/auth-provider";
import { ApiError } from "@/shared/lib/api-client";

export default function LoginPage() {
  const { login, isLoggingIn, isAuthenticated } = useAuth();
  const router = useRouter();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (isAuthenticated === true) router.replace("/dashboard");
  }, [isAuthenticated, router]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    try {
      await login(email, password);
      router.replace("/dashboard");
    } catch (error) {
      if (error instanceof ApiError) {
        setFormError(
          error.status === 401
            ? "E-mail ou senha inválidos."
            : error.status === 403
              ? "Acesso bloqueado. Fale com o administrador do tenant."
              : error.status === 429
                ? "Muitas tentativas. Aguarde um instante e tente novamente."
                : error.message
        );
      } else {
        setFormError("Não foi possível conectar ao servidor.");
      }
    }
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-muted/40 p-6">
      <Card className="w-full max-w-sm">
        <CardHeader className="items-center text-center">
          <div className="mb-2 flex h-11 w-11 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Truck className="h-5 w-5" />
          </div>
          <CardTitle>GestorFrete</CardTitle>
          <CardDescription>Entre com sua conta para continuar</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="email">E-mail</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">Senha</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </div>
            {formError ? <p className="text-sm text-destructive">{formError}</p> : null}
            <Button type="submit" className="mt-1" disabled={isLoggingIn}>
              {isLoggingIn ? "Entrando..." : "Entrar"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
