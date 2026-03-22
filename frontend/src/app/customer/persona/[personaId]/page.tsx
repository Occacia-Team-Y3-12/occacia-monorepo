import CustomerPersonaPage from '@/components/features/customer/persona/CustomerPersonaPage';

type CustomerPersonaDetailRouteProps = {
  params: Promise<{
    personaId: string;
  }>;
};

export default async function CustomerPersonaDetailRoute({
  params,
}: CustomerPersonaDetailRouteProps) {
  const { personaId } = await params;

  return <CustomerPersonaPage personaId={personaId} />;
}
