export default interface VisitDataType {
        id: number;
        patientInternalId: number;
        patientIdNumber: string;
        bookingRefNumber: string;
        visitStatus: string;
        dateVisited: string;
        timeVisited: string;
        doctorId: number;
        hospitalId: number;
        departmentId: number;
        date_created: string;
        date_opened: string;
        bookingId: number;
        hospitalName?: string;
        departmentName?: string;
        doctorName?: string;
        doctorSurname?: string;
      }