import { PatientDataType } from './Patient';
     import { VisitDataType } from './Visit';

     export default interface BookingDataType {
       id: number;
       patientInternalId: number;
       patientIdNumber: string;
       patientNationalID: string;
       bookingRef: string;
       dateBooked: string;
       timeBooked: string;
       bookingStatus: string;
       hospitalId: number;
       doctorId: number;
       departmentId: number;
       date_created: string;
       date_opened: string;
       hospitalName?: string;
       departmentName?: string;
       doctorName?: string;
       doctorSurname?: string;
       visits?: VisitDataType[];
       patient?: PatientDataType;
     }