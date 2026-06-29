export const formatMetric = (value:number) => new Intl.NumberFormat("en",{notation:Math.abs(value)>=1000?"compact":"standard",maximumFractionDigits:1}).format(value);
export const formatDate = (value:string) => new Intl.DateTimeFormat("en",{dateStyle:"medium"}).format(new Date(value));
