export default function VocabTable({ data }) {
    return (
      <table className="table table-hovertable table-hover">
        <thead>
          <tr>
            <th>Word</th>
            <th>Translation</th>
            <th>Count</th>
            <th>Recall</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i}>
              <td>{row.Word}</td>
              <td>{row.Translation}</td>
              <td>{row.Count}</td>
              <td>{row.Recall == null ? "-" : Number(row.Recall).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }
  
