export type CustomerTemplate = {
  title: string;
  image: string;
};

export const useCustomerDashboard = () => {
  const templates: CustomerTemplate[] = [
    { title: 'Birthday', image: '/images/customer/dashboard/birthday.svg' },
    { title: 'Anniversary', image: '/images/customer/dashboard/anniversary.svg' },
    { title: 'Farewell', image: '/images/customer/dashboard/farewell.svg' },
    { title: 'Get Together', image: '/images/customer/dashboard/get_together.svg' },
  ];

  return { templates };
};
