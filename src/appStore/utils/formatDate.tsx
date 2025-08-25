type obj = Partial<{
       date_created: string;
       date_opened: string;
       dateBooked: string;
     }>;

     type ArrayOrStr<T extends obj | string> = T extends obj ? T[] : string;

     function formatDate<T extends obj>(array: T[]) {
       return [];
     }

     export default formatDate;

     export const formatStringDate = (d: string) => {
       return '';
     };