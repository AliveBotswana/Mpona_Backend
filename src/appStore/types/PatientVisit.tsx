import { VisitDataType } from './Visit';
     import { BookingDataType } from './Booking';

     export default interface PatientVisitDataType extends VisitDataType {
       booking: BookingDataType;
     }