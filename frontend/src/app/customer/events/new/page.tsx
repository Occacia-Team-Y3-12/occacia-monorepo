import CustomerCreateEvent from '@/components/features/customer/CustomerCreateEvent';

type CustomerNewEventPageProps = {
  searchParams?: Promise<{
    template?: string | string[];
  }>;
};

export default async function CustomerNewEventPage({
  searchParams,
}: CustomerNewEventPageProps) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const templateValue = resolvedSearchParams?.template;
  const initialTemplate = Array.isArray(templateValue)
    ? templateValue[0]
    : templateValue;

  return <CustomerCreateEvent initialTemplate={initialTemplate} />;
}
