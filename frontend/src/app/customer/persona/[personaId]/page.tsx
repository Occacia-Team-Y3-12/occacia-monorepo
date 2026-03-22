import PersonaEditPage from '@/components/features/customer/persona/PersonaEditPage';

type CustomerPersonaDetailRouteProps = {
  params: Promise<{
    personaId: string;
  }>;
};

export default async function CustomerPersonaDetailRoute({
  params,
}: CustomerPersonaDetailRouteProps) {
  const { personaId } = await params;

  return <PersonaEditPage mode="edit" personaId={personaId} />;
}
